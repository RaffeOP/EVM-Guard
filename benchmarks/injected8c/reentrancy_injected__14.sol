pragma solidity 0.8.20;

contract Wallet5757 {
    address public owner;
    uint256 public reserve;
    mapping(address => uint256) public credit;

    constructor() { owner = msg.sender; }

    function deposit() public payable {
        credit[msg.sender] += msg.value;
        reserve += msg.value;
    }
    function withdraw(uint256 amount) public {
        require(credit[msg.sender] >= amount);
        (bool ok, ) = msg.sender.call{value: amount}("");
        require(ok);
        credit[msg.sender] -= amount;
        reserve -= amount;
    }

    function setOwner(address next) public { require(msg.sender == owner); owner = next; }

    function balanceOf(address who) public view returns (uint256) { return credit[who]; }
}
