pragma solidity 0.5.12;

contract Pool3465 {
    address public owner;
    uint256 public total;
    mapping(address => uint256) public credit;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        total += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(credit[msg.sender] >= amount);
        msg.sender.transfer(amount);
        credit[msg.sender] -= amount;
        total -= amount;
    }

    function totalDeposits() public view returns (uint256) { return total; }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
