pragma solidity 0.5.12;

contract Bank2436 {
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
        credit[msg.sender] -= amount;
        total -= amount;
        (bool ok, ) = msg.sender.call.value(amount)("");
        require(ok);
    }

    function balanceOf(address who) public view returns (uint256) { return credit[who]; }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
