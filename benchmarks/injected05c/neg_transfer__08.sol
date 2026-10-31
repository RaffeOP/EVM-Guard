pragma solidity 0.5.12;

contract Bank3264 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public balances;

    constructor() public { owner = msg.sender; }

    function deposit() public payable {
        balances[msg.sender] += msg.value;
        reserve += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(balances[msg.sender] >= amount);
        msg.sender.transfer(amount);
        balances[msg.sender] -= amount;
        reserve -= amount;
    }

    function balanceOf(address who) public view returns (uint256) { return balances[who]; }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }
}
