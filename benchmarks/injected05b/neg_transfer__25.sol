pragma solidity 0.5.12;

contract Safe7078 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public shares;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        shares[msg.sender] += msg.value;
        reserve += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(shares[msg.sender] >= amount);
        msg.sender.transfer(amount);
        shares[msg.sender] -= amount;
        reserve -= amount;
    }

    function totalDeposits() public view returns (uint256) { return reserve; }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
